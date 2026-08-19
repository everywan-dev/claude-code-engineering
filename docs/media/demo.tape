Output demo.gif
Set Theme "Catppuccin Mocha"
Set FontSize 20
Set Width 1180
Set Height 620
Set Padding 24
Set TypingSpeed 32ms

Hide
Type "source .demorc" Enter
Show

Sleep 600ms
Type "# A fact, and how we know it" Sleep 700ms Enter
Type "head -12 knowledge/kb-0001-db-failover.md" Enter
Sleep 3s

Type "# 'hypothesis' means: nobody checked. It says so." Sleep 900ms Enter
Type "validated-memory validate" Enter
Sleep 2500ms

Type "# Now someone gets creative with the frontmatter" Sleep 800ms Enter
Type "sed -i '' 's/^provenance:/provenance: >-/' knowledge/kb-0001-db-failover.md" Enter
Sleep 900ms
Type "validated-memory validate" Enter
Sleep 3500ms

Type "# Caught. Run it in CI and it cannot merge." Sleep 1200ms Enter
Sleep 1500ms
