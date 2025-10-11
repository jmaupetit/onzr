Onzr can be set either by defining environment variables or a configuration
file.

This configuration file respects general and specific rules that we will
describe in detail in the following sections.

## General rules

### Use `onzr init` to bootstrap your configuration

Onzr CLI comes with a `init` command that can help you boostraping your project
(see the [tutorial](./tutorial.md)). Remember that the `onzr init` command will
generate the configuration file for you. Once generated it's up to you to
change setting values to suit your needs.

### Configuration file location

Onzr configuration file is stored inside your user's application folder.
Depending on your system, the default path is likely:

- MacOSX: `~/Library/Application Support/onzr/settings.yaml`
- Windows: `%appdata%\onzr\settings.yaml`, which usually expands to
  `C:\Users\<user>\AppData\Roaming\onzr\settings.yaml`
- Linux: `~/.config/onzr/settings.yaml`

### Settings can be overridden using environment variables

Every setting can be overridden by defining the corresponding environment
variable (in uppercase) prefixed by `ONZR_`, _e.g._ for the `DEBUG` setting,
you can define the `ONZR_DEBUG=true` environment variable to override the
value defined in the `settings.yaml` file.

## Configuration details

### `ARL`

This is an authentication token provided by Deezer to connect to the Deezer
gateway API.

!!! Info

    You can find this token by following [this
    guide](https://github.com/nathom/streamrip/wiki/Finding-Your-Deezer-ARL-Cookie).

---

### `QUALITY`

Default track encoding quality that will be streamed.

Default: `MP3_128`

!!! info

    Allowed values are:

    - `MP3_128`
    - `MP3_320`
    - `FLAC`

---

### `DEBUG`

Set to `true` to enable debugging mode, CLI messages and server logs will be
more explicit.

Default: `false`

!!! Warning

    We strongly recommend to keep default `false` value when running Onzr outside from development.

---

### `SCHEMA`

The server URL schema.

Default: `http`

---

### `HOST`

This is the host socket will be bind to. It can be an IPv4 or IPv6 address, or a
fully qualified domain name (_e.g._ `onzr.example.org`). Set this to `0.0.0.0`
if you want your application to be available from your local network.

Default: `localhost`

---

### `PORT`

This the host port the socket will be bind to.

Default: `9473`

---

### `API_ROOT_URL`

This the root URL Onzr server will respond from.

Default: `/api/v1`

---

### `TRACK_STREAM_ENDPOINT`

The URL pattern used for the track stream endpoint.

!!! Tip

    The `rank` variable is supposed to be injected in the template.

Default: `/queue/{rank}/stream`

---

### `DEEZER_BLOWFISH_SECRET`

This secret is used to decrypt Deezer track stream on the fly.

!!! Danger

    This secret is distributed with Onzr and is **not** supposed to be changed.
    You won't be able to stream your music if this value is falsy.
