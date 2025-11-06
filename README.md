Run the Efinix / Efinity software in a docker image.

Put your authentication token in the .token file if your docker
doesn't propagate the authentication tokens.

Explicitly enable modifying the host system with `-o`:

```bash
dagger call efinity-get --token=file://.token  -o outflow
```

All rights reserved where indicated. Otherwise re-use at will.

