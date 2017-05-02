# via http://apple.stackexchange.com/questions/136118/how-to-print-full-presenter-notes-without-slides-in-keynote
global presenterNotes
tell application "Keynote"
    activate
    open (choose file)
    tell front document
        set presenterNotes to presenter notes of every slide as text
            set the clipboard to presenterNotes
        do shell script "pbpaste > ~/keynote-notes.txt"
    end tell    
    quit application "Keynote"
end tell