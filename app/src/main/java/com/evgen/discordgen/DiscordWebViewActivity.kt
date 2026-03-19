package com.evgen.discordgen

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.webkit.*
import android.widget.Button
import android.widget.TextView
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity

class DiscordWebViewActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var tvStatus: TextView
    private lateinit var btnVerificationDone: Button
    private lateinit var btnViewResults: Button

    private lateinit var aliases: List<String>
    private lateinit var discordPassword: String
    private lateinit var gmail: String

    private var currentIndex = 0
    private var capturedToken: String? = null
    private var waitingForVerification = false

    // JS injection runs once per page that contains the Discord register form
    private var jsInjected = false

    companion object {
        // Chrome 124 UA – update minor version periodically to stay current
        private const val CHROME_UA =
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36"
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_discord_webview)

        webView = findViewById(R.id.webView)
        tvStatus = findViewById(R.id.tvStatus)
        btnVerificationDone = findViewById(R.id.btnVerificationDone)
        btnViewResults = findViewById(R.id.btnViewResults)

        gmail = intent.getStringExtra("gmail") ?: ""
        discordPassword = intent.getStringExtra("discord_password") ?: ""
        aliases = intent.getStringArrayListExtra("aliases") ?: emptyList()

        setupWebView()

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack()) webView.goBack() else finish()
            }
        })

        btnVerificationDone.setOnClickListener {
            btnVerificationDone.visibility = View.GONE
            waitingForVerification = false
            currentIndex++
            processNextAlias()
        }

        btnViewResults.setOnClickListener {
            startActivity(Intent(this, DownloadActivity::class.java))
        }

        processNextAlias()
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            userAgentString = CHROME_UA
            loadWithOverviewMode = true
            useWideViewPort = true
            setSupportZoom(true)
            builtInZoomControls = true
            displayZoomControls = false
            cacheMode = WebSettings.LOAD_DEFAULT
            mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
        }

        webView.webChromeClient = object : WebChromeClient() {
            override fun onJsAlert(view: WebView, url: String, message: String, result: JsResult): Boolean {
                result.confirm()
                return true
            }
            override fun onJsConfirm(view: WebView, url: String, message: String, result: JsResult): Boolean {
                result.confirm()
                return true
            }
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                // Stay in-app
                return false
            }

            override fun onPageStarted(view: WebView, url: String, favicon: android.graphics.Bitmap?) {
                jsInjected = false
                // Detect navigation away from /register – save with note if token was missed
                if (!url.contains("/register") && capturedToken == null && !waitingForVerification) {
                    val alias = aliases.getOrNull(currentIndex) ?: return
                    log("Navigated away from /register – token not captured for $alias")
                    // Do NOT save to tokens.txt/acc.txt without a real token; just log and proceed
                }
            }

            override fun onPageFinished(view: WebView, url: String) {
                when {
                    url.contains("discord.com/register") && !jsInjected -> {
                        jsInjected = true
                        injectRegisterForm()
                    }
                    url.contains("mail.google.com") && waitingForVerification -> {
                        log("Gmail loaded – please verify email then tap the button")
                        btnVerificationDone.visibility = View.VISIBLE
                    }
                    url.contains("discord.com") && !url.contains("/register") && !waitingForVerification -> {
                        // Successfully registered, now go to Gmail for verification
                        if (capturedToken != null) {
                            log("Registration successful! Token captured.")
                        }
                        goToGmailVerification()
                    }
                }
            }

            override fun shouldInterceptRequest(
                view: WebView,
                request: WebResourceRequest
            ): WebResourceResponse? {
                val urlStr = request.url.toString()
                if (urlStr.contains("/api/") && urlStr.contains("/auth/register")) {
                    // We can't read response bodies from shouldInterceptRequest on standard Android WebView.
                    // Token capture is handled via JavascriptInterface injected into the page instead.
                }
                return super.shouldInterceptRequest(view, request)
            }
        }

        // Add JavaScript interface for token capture
        webView.addJavascriptInterface(TokenBridge(), "AndroidBridge")
    }

    inner class TokenBridge {
        @JavascriptInterface
        fun onTokenCaptured(token: String) {
            if (token.isNotBlank() && capturedToken == null) {
                capturedToken = token
                runOnUiThread {
                    log("Token captured for ${aliases.getOrNull(currentIndex)}")
                    val alias = aliases.getOrNull(currentIndex) ?: return@runOnUiThread
                    saveAccount(alias, token)
                    goToGmailVerification()
                }
            }
        }

        @JavascriptInterface
        fun onLog(message: String) {
            runOnUiThread { log("[JS] $message") }
        }
    }

    private fun processNextAlias() {
        if (currentIndex >= aliases.size) {
            log("All ${aliases.size} account(s) processed!")
            tvStatus.text = "All done!"
            btnViewResults.visibility = View.VISIBLE
            return
        }
        capturedToken = null
        jsInjected = false
        val alias = aliases[currentIndex]
        tvStatus.text = "Account ${currentIndex + 1}/${aliases.size}: registering $alias"
        log("Loading Discord register for $alias")
        webView.loadUrl("https://discord.com/register")
    }

    private fun injectRegisterForm() {
        val alias = aliases.getOrNull(currentIndex) ?: return
        val username = alias.substringBefore('@')
            .replace('+', '_')
            .take(32)
        val password = escapeJs(discordPassword)
        val emailEscaped = escapeJs(alias)

        // Month/Day/Year for DOB – use a fixed adult date
        val dobMonth = "January"
        val dobDay = "15"
        val dobYear = "1995"

        val js = """
(function() {
  function setNativeValue(el, value) {
    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
    nativeInputValueSetter.call(el, value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }
  function setSelectValue(sel, value) {
    sel.value = value;
    sel.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function tryFill(attempt) {
    if (attempt > 20) {
      AndroidBridge.onLog('Form not found after 20 attempts – giving up');
      return;
    }
    var emailEl = document.querySelector('input[name="email"]');
    var passwordEl = document.querySelector('input[name="password"]');
    var usernameEl = document.querySelector('input[name="global_name"]') ||
                     document.querySelector('input[name="username"]');
    if (!emailEl || !passwordEl || !usernameEl) {
      AndroidBridge.onLog('Form not ready yet, retrying… (' + attempt + '/20)');
      setTimeout(function() { tryFill(attempt + 1); }, 1000);
      return;
    }
    setNativeValue(emailEl, '$emailEscaped');
    setNativeValue(usernameEl, '${escapeJs(username)}');
    setNativeValue(passwordEl, '$password');
    AndroidBridge.onLog('Form fields filled');

    // DOB selects – Discord uses custom UI; try both select and aria approaches
    var selects = document.querySelectorAll('select');
    if (selects.length >= 3) {
      setSelectValue(selects[0], '$dobMonth');
      setSelectValue(selects[1], '$dobDay');
      setSelectValue(selects[2], '$dobYear');
      AndroidBridge.onLog('DOB set via selects');
    }

    // Intercept fetch to capture token from register response
    var origFetch = window.fetch;
    window.fetch = function() {
      var args = arguments;
      return origFetch.apply(this, args).then(function(response) {
        var url = (args[0] && args[0].url) ? args[0].url : (typeof args[0] === 'string' ? args[0] : '');
        if (url && url.indexOf('/auth/register') !== -1 && response.status === 201) {
          response.clone().json().then(function(data) {
            if (data && data.token) {
              AndroidBridge.onTokenCaptured(data.token);
            }
          }).catch(function(e) {});
        }
        return response;
      });
    };
    AndroidBridge.onLog('fetch interceptor installed');
  }

  setTimeout(function() { tryFill(1); }, 1500);
})();
        """.trimIndent()

        webView.evaluateJavascript(js, null)
    }

    private fun goToGmailVerification() {
        if (!waitingForVerification) {
            waitingForVerification = true
            val alias = aliases.getOrNull(currentIndex) ?: return
            log("Opening Gmail for verification of $alias")
            tvStatus.text = "Account ${currentIndex + 1}/${aliases.size}: verify email in Gmail"
            webView.loadUrl("https://mail.google.com")
        }
    }

    private fun saveAccount(email: String, token: String) {
        TokenStore.appendToken(this, token)
        TokenStore.appendAccount(this, email, discordPassword, token)
        log("Saved: $email → $token")
    }

    private fun log(message: String) {
        MainActivity.postLog(message)
    }

    private fun escapeJs(s: String): String =
        s.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace("\n", "\\n")
            .replace("\r", "\\r")

}
