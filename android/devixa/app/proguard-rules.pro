# Devixa exposes no JavaScript-to-native bridge. Keep only the activity and
# WebView callback classes referenced by Android framework reflection.
-keep class ir.acdevixa.devixa.MainActivity { *; }
-keep class ir.acdevixa.devixa.web.** { *; }

# Retain useful line information for Play Console deobfuscation diagnostics.
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
