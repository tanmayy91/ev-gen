package com.evgen.discordgen

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.textfield.TextInputEditText

class MainActivity : AppCompatActivity() {

    companion object {
        // Static log buffer so DiscordWebViewActivity can append messages
        val logLines = mutableListOf<String>()
        var logCallback: ((String) -> Unit)? = null

        fun postLog(message: String) {
            logLines.add(message)
            logCallback?.invoke(message)
        }
    }

    private lateinit var etGmail: TextInputEditText
    private lateinit var etGmailPassword: TextInputEditText
    private lateinit var etDiscordPassword: TextInputEditText
    private lateinit var etCount: TextInputEditText
    private lateinit var tvLog: TextView
    private lateinit var scrollLog: ScrollView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        etGmail = findViewById(R.id.etGmail)
        etGmailPassword = findViewById(R.id.etGmailPassword)
        etDiscordPassword = findViewById(R.id.etDiscordPassword)
        etCount = findViewById(R.id.etCount)
        tvLog = findViewById(R.id.tvLog)
        scrollLog = findViewById(R.id.scrollLog)

        // Replay any existing log lines (e.g. after coming back from WebView)
        refreshLog()

        logCallback = { msg ->
            runOnUiThread {
                tvLog.append("$msg\n")
                scrollLog.post { scrollLog.fullScroll(ScrollView.FOCUS_DOWN) }
            }
        }

        findViewById<Button>(R.id.btnStart).setOnClickListener { onStartClicked() }
        findViewById<Button>(R.id.btnViewResults).setOnClickListener {
            startActivity(Intent(this, DownloadActivity::class.java))
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        logCallback = null
    }

    private fun refreshLog() {
        tvLog.text = logLines.joinToString("\n")
        if (logLines.isNotEmpty()) {
            scrollLog.post { scrollLog.fullScroll(ScrollView.FOCUS_DOWN) }
        }
    }

    private fun onStartClicked() {
        val gmail = etGmail.text?.toString()?.trim() ?: ""
        val gmailPassword = etGmailPassword.text?.toString() ?: ""
        val discordPassword = etDiscordPassword.text?.toString() ?: ""
        val countStr = etCount.text?.toString()?.trim() ?: ""

        if (gmail.isEmpty() || !gmail.contains('@')) {
            Toast.makeText(this, "Enter a valid Gmail address", Toast.LENGTH_SHORT).show()
            return
        }
        if (gmailPassword.isEmpty()) {
            Toast.makeText(this, "Enter your Gmail password", Toast.LENGTH_SHORT).show()
            return
        }
        if (discordPassword.length < 8) {
            Toast.makeText(this, "Discord password must be at least 8 characters", Toast.LENGTH_SHORT).show()
            return
        }
        val count = countStr.toIntOrNull()
        if (count == null || count !in 1..50) {
            Toast.makeText(this, "Account count must be between 1 and 50", Toast.LENGTH_SHORT).show()
            return
        }

        val aliases = AliasGenerator.generateAliases(gmail, count)
        postLog("Generated $count alias(es). Starting…")

        val intent = Intent(this, DiscordWebViewActivity::class.java).apply {
            putExtra("gmail", gmail)
            putExtra("gmail_password", gmailPassword)
            putExtra("discord_password", discordPassword)
            putStringArrayListExtra("aliases", ArrayList(aliases))
        }
        startActivity(intent)
    }
}
