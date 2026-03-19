package com.evgen.discordgen

object AliasGenerator {

    private val CHARS = ('a'..'z') + ('0'..'9')

    /**
     * Generates [count] unique Gmail+ alias addresses from [baseEmail].
     * Strips any existing +… suffix from the local part before appending
     * a fresh 4-character random alphanumeric suffix.
     */
    fun generateAliases(baseEmail: String, count: Int): List<String> {
        val atIndex = baseEmail.indexOf('@')
        if (atIndex < 0) return emptyList()

        val domain = baseEmail.substring(atIndex)           // e.g. @gmail.com
        val localFull = baseEmail.substring(0, atIndex)     // e.g. tanmayyy911+old
        val local = localFull.substringBefore('+')          // e.g. tanmayyy911

        val usedSuffixes = mutableSetOf<String>()
        val result = mutableListOf<String>()

        while (result.size < count) {
            val suffix = buildString {
                repeat(4) { append(CHARS.random()) }
            }
            if (usedSuffixes.add(suffix)) {
                result.add("$local+$suffix$domain")
            }
        }
        return result
    }
}
