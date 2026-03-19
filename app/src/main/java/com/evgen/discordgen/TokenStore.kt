package com.evgen.discordgen

import android.content.Context
import java.io.File
import java.io.IOException

object TokenStore {

    private fun getDir(context: Context): File =
        context.getExternalFilesDir(null) ?: context.filesDir

    fun getTokensFile(context: Context): File =
        File(getDir(context), "tokens.txt")

    fun getAccountsFile(context: Context): File =
        File(getDir(context), "acc.txt")

    fun appendToken(context: Context, token: String) {
        try {
            getTokensFile(context).appendText("$token\n")
        } catch (e: IOException) {
            e.printStackTrace()
        }
    }

    fun appendAccount(context: Context, email: String, password: String, token: String) {
        try {
            getAccountsFile(context).appendText("$email:$password:$token\n")
        } catch (e: IOException) {
            e.printStackTrace()
        }
    }

    fun readTokens(context: Context): String =
        try { getTokensFile(context).readText() } catch (e: IOException) { "" }

    fun readAccounts(context: Context): String =
        try { getAccountsFile(context).readText() } catch (e: IOException) { "" }
}
