Output quick-start.gif

Source ./scripts/config.tape 
Set LoopOffset 2

Hide
Type "figlet -f big '  ONZR - Demo ' | lolcat"
Enter
Show
Sleep 2s

Ctrl+l

# Start onzr server
Type@50ms "# Run Onzr server in the background"
Ctrl+c
Enter
Sleep 300ms
Type "onzr serve --log-level error &"
Sleep 300ms
Enter
Sleep 1s

Ctrl+l

Type@50ms "# Look for Billie Eilish latest album"
Ctrl+c
Enter
Sleep 300ms
Type "onzr search --artist 'Billie Eilish'"
Sleep 300ms
Enter
Sleep 3s 

Up
Type " --ids --first | \"
Enter
Type "onzr artist --albums -"
Sleep 300ms
Enter
Sleep 4s

Enter
Type@50ms "# Get latest Billie Eilish album tracks"
Ctrl+c
Enter
Sleep 300ms
Up
Type " --limit 1 --ids | \"
Enter
Type "onzr album -"
Sleep 300ms
Enter
Sleep 4s 

Enter
Type@50ms "# Add tracks to Onzr queue"
Ctrl+c
Enter
Sleep 300ms
Up
Type " --ids | \" 
Enter 
Type "onzr add -"
Sleep 300ms
Enter
Sleep 4s 

Enter
Type@50ms "# Start playing"
Ctrl+c
Enter
Sleep 300ms
Type "onzr play"
Sleep 300ms
Enter
Sleep 4s 

Ctrl+l
Sleep 300ms 

Type@50ms "# Display track progress live!"
Ctrl+c
Enter
Sleep 300ms
Type "onzr now -f"
Enter
Sleep 6s
Ctrl+c
 
Sleep 1s
Enter
Type "echo '🎵 Happy listening with onzr 🎶' | lolcat"
Enter
Sleep 4s
Ctrl+l 
