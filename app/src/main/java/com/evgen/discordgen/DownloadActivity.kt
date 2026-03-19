package com.evgen.discordgen

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.FileProvider

class DownloadActivity : AppCompatActivity() {

    private lateinit var tvTokens: TextView
    private lateinit var tvAccounts: TextView
    private lateinit var scrollTokens: ScrollView
    private lateinit var scrollAccounts: ScrollView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_download)

        tvTokens = findViewById(R.id.tvTokens)
        tvAccounts = findViewById(R.id.tvAccounts)
        scrollTokens = findViewById(R.id.scrollTokens)
        scrollAccounts = findViewById(R.id.scrollAccounts)

        loadContent()

        findViewById<Button>(R.id.btnShareTokens).setOnClickListener { shareFile("tokens") }
        findViewById<Button>(R.id.btnShareAccounts).setOnClickListener { shareFile("accounts") }
        findViewById<Button>(R.id.btnBack).setOnClickListener { finish() }
        findViewById<Button>(R.id.btnRefresh).setOnClickListener { loadContent() }
    }

    private fun loadContent() {
        val tokens = TokenStore.readTokens(this)
        val accounts = TokenStore.readAccounts(this)

        tvTokens.text = tokens.ifEmpty { "(empty)" }
        tvAccounts.text = accounts.ifEmpty { "(empty)" }

        scrollTokens.post { scrollTokens.fullScroll(ScrollView.FOCUS_DOWN) }
        scrollAccounts.post { scrollAccounts.fullScroll(ScrollView.FOCUS_DOWN) }
    }

    private fun shareFile(type: String) {
        val file = when (type) {
            "tokens" -> TokenStore.getTokensFile(this)
            else -> TokenStore.getAccountsFile(this)
        }

        if (!file.exists() || file.length() == 0L) {
            Toast.makeText(this, "No data to share yet", Toast.LENGTH_SHORT).show()
            return
        }

        try {
            val uri = FileProvider.getUriForFile(
                this,
                "${packageName}.fileprovider",
                file
            )
            val intent = Intent(Intent.ACTION_SEND).apply {
                type = "text/plain"
                putExtra(Intent.EXTRA_STREAM, uri)
                addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            }
            startActivity(Intent.createChooser(intent, "Share ${file.name}"))
        } catch (e: Exception) {
            Toast.makeText(this, "Error sharing file: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }
}
