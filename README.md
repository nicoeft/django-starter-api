# django-starter-api

A boilerplate for creating REST API with Django and Django Rest Framework.

## Development

```bash
docker-compose -f local.yml build
docker-compose -f local.yml up
```

If you want, you can export `COMPOSE_FILE` so you don't have to write `-f local.yml` every time you want to run a docker command.
```
export COMPOSE_FILE=local.yml

docker-compose build
docker-compose up
docker-compose ps
docker-compose down
```

## Create superuser

```
docker-compose -f local.yml run --rm django python manage.py createsuperuser
```

## Contributing

I'll be happily accepting pull requests from anyone.

This that are missing right now:

* [ ] Add tests and coverage implementations
* [ ] Remove weak Token Authorization system

Suggestions are welcome!


## Contributors

- [Marcos Aguayo](https://github.com/maguayo)
  | Senior Python Developer | <marcos@aguayo.es>
