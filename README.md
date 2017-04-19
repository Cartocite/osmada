Osmada − OpenStreetMap Adiff Analyzer
=====================================

Installing
----------

The most convenient is to use a Python virtualenv.

### Install virtualenv itself

eg ; on Debian-like :

    # apt install python3 virtualenv

On Ubuntu

    # sudo apt-get install python3 virtualenv

### Create the virtualenv
On Windows

    $ mkvirtualenv --python=/usr/bin/python3 ./venv

On Ubuntu

    $ virtualenv --python=/usr/bin/python3 ./venv


### Enter the virtualenv

Be sure to be inside the venv before running any osmada command or install
dependencies. To enter the venv :

    $ source venv/bin/activate

Notice the `(venv)` at the beggining on your shell prompt.

### Install the dependencies

    (venv) $ pip install -r requirements.txt


Create the database :

    $ ./manage.py migrate

You're good to go !


Using it
--------

### Commands

*osmada* is mainly a CLI tool.

They are defined as django commands ; thus they run as:

    $ ./manage.py <command name>

To get command list:

    $ ./manage.py help

Get help about a specific command:

    $ ./manage.py help <command name>

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

Default settings are stored in *osmada/settings.py* ; do not edit this
file.

To start overriding settings :

    $ cp osmada/local_settings.py.example osmada/local_settings.py

And edit *osmada/local_settings.py* to suit your needs ; the example file
is commented and used to document the setting keys.

Advanced
--------

### Running unit tests

Hint : run them each time you modify the code, and better: add tests for your
code.

Initial setup:

    $ pip install -r test-requirements.txt

Run tests:

    $ ./manage.py test --settings=osmada.base_settings

See coverage:

    $ coverage run manage.py test --settings=osmada.base_settings
    $ coverage report

### How long does my workflow takes ?

Use the `time` command to figure out.

    $ time ./manage.py workflow ...

### Use with cron / scripts

To call *manage.py* commands from cron or shell scripts ; you may want to write
something like:

    /path/to/your/venv/bin/python /path/to/your/manage.py command ...

### What about treating a whole folder of adiff ?

Bash to the rescue (example) :

    $ for f in /home/steve/*.osm; do ./manage.py workflow passthrough "$f" > "/tmp/`basename -s.osm ${f}`.adiff" ; done
