# 思い出ギャラリー

https://memories-gallery.herokuapp.com

## Development

### Server 1

```
$ python3 app.py
```

### Server 2

```
$ postgres -D /usr/local/var/postgres
```

### Server 3

```
$ createdb gallery
$ python3

>>> from app import db
>>> db.create_all()

$ dropdb gallery
```

## Deployment

```
$ heroku create
$ heroku addons:create heroku-postgresql:hobby-dev
$ git push heroku master
$ heroku run python

>>> from app import db
>>> db.create_all()
```
