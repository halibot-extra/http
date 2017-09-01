Halibot HTTP module
===================

Installation
------------

There are no external dependencies besides halibot and python, so all that is
required is:

```bash
halibot fetch http
```

Server
------

You can add an HTTP server to your halibot instance with `halibot add http:Server`
or just `halibot add http`. There is one notable difference from other halibot agents
in that the `out` field of the config is not a list of destination modules, but rather
an object where each key is an HTTP method with a value that is a list of resource
identifiers listing what modules to receive messages for that method.

In the following example, module `a` only receives `GET` requests, while `c` only receives
`POST` requests, and `b` receives both.
```json
"out": {
	"GET": [ "a", "b" ],
	"POST": [ "b", "c" ]
}
```

Client
------

To be implemented
