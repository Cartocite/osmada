Cartowatch − Watch OpenStreetMap edits
======================================

Installing
----------

The most convenient is to use a Python virtualenv.

### Install virtualenv itself

eg ; on Debian-like :

    # apt instal python3 python3-virtualenv

### Create the virtualenv

    $ mkvirtualenv --python=/usr/bin/python3 ./venv


Once created, you terminal will immediatly enter the virtualenv (notice the
`(venv)` at the beggining on your shell prompt.

### Install the dependencies

    (venv) $ pip install -r requirements.txt


You're good to go !


Using it
--------

Be sure to be inside the venv before running any cartowatch command. To enter
the venv :

    $ source venv/bin/activate

### Running workflows

Workflows are the complete transformation process :

1. Load diff data from an external source into DB.
2. Apply one or several filters
3. Output as string in a given format

You can have different workflows, configured in settings. By default, you only
have one available called `passthrough` (basically useless) ; you can run it on
some adiff file of yours:

    $ ./manage.py workflow passthrough /home/steve/my_adiff.xml

It will output adiff XML code to stdout ; you may want to redirect it to some
file:

    $ ./manage.py workflow passthrough /home/steve/my_adiff.xml > out_adiff.xml


### Loading data

You may want to load data into the DB without applying an entire workflow.

    $ ./manage.py import_adiff /home/steve/my_adiff.xml


### Using web interface

There is a web interface to interactively visualize data in DB.

You first create a user:

    $ ./manage.py createsuperuser

Then you can run the local webserver


    $ ./manage.py runserver


And fire your browser to http://localhost:8000/admin

### Flushing the db

Each time you run a workflow or import data, the database fills up ; if you
want to cleanup all that :

    $ ./manage.py flush


Configuration
-------------

Default settings are stored in *cartowatch/settings.py* ; do not edit this
file.

To start overriding settings :

    $ cp cartowatch/local_settings.py.example cartowatch/local_settings.py

And edit *cartowatch/local_settings.py* to suit your needs ; the example file
is commented and used to document the setting keys.

Advanced
--------

`TAGS_IMPORTANCE` Allows to set which tags are the most important to you ; that
may be used to guess a "main tag" to qualify an action.

E.g:

```
TAGS_IMPORTANCE = [railway=*', 'indor=area', 'amenity=*', ]

```
