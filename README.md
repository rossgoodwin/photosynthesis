# photosynthesis

Built for the [word.camera](http://word.camera) image-to-text translator by [Ross Goodwin](http://rossgoodwin.com)


## License Information

word.camera image-to-text translator
Copyright  (C) 2015  Ross Goodwin
 
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
 
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
 
You can contact Ross Goodwin at ross.goodwin@gmail.com or address
physical correspondence and verbal abuse to:
 
Ross Goodwin c/o ITP
721 Broadway
4th Floor
New York, NY 10003


## Cautionary Preamble

I developed this project as a creative exercise rather than an engineering task. As a result, it is a total mess. Full disclosure: I wrote this code very quickly. I didn't leave many comments. If you are about to dive into my [__init__.py](https://github.com/rossgoodwin/photosynthesis/blob/master/__init__.py) file, which is the main file for this program, I apologize in advance. 

This is the current version of the code that is running live on word.camera's web server, so please do not be offended if I do not accept your pull request.


## Running Your Own Copy

In theory, following these steps should allow you to run your own copy of the word.camera software on a Unix-based operating system (word.camera is running this software on Ubuntu 14.04):

1. Clone this repository.
2. Create a virtualenv and run `pip install -r requirements.txt`
3. Create new empty directories at `static/img/` and `static/output/` -- these folders are for processed images and rendered html files, respectively.
4. Download the [Clarifai Python API wrapper](https://github.com/Clarifai/Clarifai_py), change that folder's name to `py` (or change the import line in `__init__.py`), create a [Clarifai API](http://clarifai.com) account, and set environmental variables to match your API key and secret following procedures described in [the library's README file](https://github.com/Clarifai/Clarifai_py/blob/master/README.md).
5. Download a local copy of the [ConceptNet5](http://conceptnet5.media.mit.edu/) database, following [the recommended procedure](https://github.com/commonsense/conceptnet5/wiki/Running-your-own-copy), and run an instance of the API server at `127.0.0.1:8084`. (If you try to change the endpoint URL to MIT's ConceptNet5 API server rather than downloading your own copy, the rate limit may restrict you.)
6. Change the following global variables in `__init__.py` to match the filepaths on your machine: `SYSPATH`, `APPPATH`, `app.config['UPLOAD_FOLDER']` (all directly below the imports at the top of the file)
7. Change the `BASEURL` global variable in `__init__.py` to match the IP or domain where you plan to run your server.
8. Add a `salty.py` file in the main directory with one variable, `saline`, set equal to a string of your choice (to seed unique URL hash values).
9. Run `python __init__.py` or set up a WSGI server. (word.camera uses [apache2](http://httpd.apache.org/) for the web server and [gunicorn](http://gunicorn.org/) for the ConceptNet server on localhost.)


Good luck, and [enjoy](http://word.camera/i/DEdwqKR3J)!


____

[Polaroid camera icon](https://thenounproject.com/term/camera/3987/) created by [Simon Child](https://thenounproject.com/Simon%20Child) (London, GB 2012) for [the Noun Project](https://thenounproject.com/)
