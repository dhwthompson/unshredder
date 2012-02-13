Unshredder
==========

This is my current attempt to solve Instagram’s [engineering challenge][ec].

[ec]: http://instagram-engineering.tumblr.com/post/12651721845/instagram-engineering-challenge-the-unshredder


Quick start
-----------

    virtualenv .
    pip install -r requirements.txt 
    python unshredder.py input/collie.png output/collie.png


Known issues
------------

Well, yeah, this is a bit embarrassing. It works on all the sample images I’ve
tried it with, *except* the one Instagram provided. I choose to blame that gurt
big striped black-and-white tower. Or my heuristic. But probably the tower.
