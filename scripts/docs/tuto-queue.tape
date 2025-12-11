Source scripts/config.tape

Hide
Type "onzr serve --log-level error &"
Enter
Type "onzr search --artist "Radiohead" --ids --first | \" 
Enter
Type "onzr artist --top --ids - | \"
Enter
Type "onzr add -"
Enter
Show
Sleep 2s

Ctrl+l 
Sleep 300ms

Type "onzr queue"
Enter 
Sleep 5s 
Type "q"
Enter 
Sleep 300ms

Type "onzr play --rank 7"
Sleep 300ms 
Enter 
Sleep 2s 

Type "onzr queue"
Enter 
Sleep 5s 
Type "q"
Enter 
Sleep 1s
