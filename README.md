# music_snapshot
[![Package Version](https://img.shields.io/pypi/v/music_snapshot)][pypi music_snapshot]
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/music_snapshot)][pypi music_snapshot]
[![Codecov](https://img.shields.io/codecov/c/github/pawelad/music_snapshot)][codecov music_snapshot]
[![License](https://img.shields.io/pypi/l/music_snapshot)][license]
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]
[![py.typed](https://img.shields.io/badge/py-typed-FFD43B)][pep561]

Save a snapshot of your day as a Spotify playlist.

[![Demo](./demo.gif)][asciicast music_snapshot]

## Installation
Since `music_snapshot` is a command line tool, the recommended installation method
is via [pipx]:

```console
$ pipx install music_snapshot
```

Of course, you can just install it directly from [PyPI] (ideally, inside a
[virtualenv]):

```console
$ python -m pip install music_snapshot
```

## Quick start

### Authentication
To use `music_snapshot` you need to authorize it with both Spotify and Last.fm.

To get Spotify client ID and secret, create an OAuth client in
[Spotify developer dashboard] (with the "Redirect URI" set to 
`http://localhost:6600/music_snapshot`).

To get Last.fm API keys, you need create a [new Last.fm API account].

After obtaining all of the above, you need to run `music_snapshot authorize`
which will save your config data in `~/.music_snapshot` and allow you to create
new music snapshots with `music_snapshot create` subcommand.

### Usage
The default subcommand is `create`, which helps you create a new music snapshot
(Spotify playlist).

You can see all available subcommands and options by running `music_snapshot --help`:

```console
$ music_snapshot --help          
                                                                                        
 Usage: music_snapshot [OPTIONS] COMMAND [ARGS]...                                      
                                                                                        
 Save a snapshot of your day as a Spotify playlist.                                     
 Have you ever just let Spotify algorithm do its thing, keep going long after your      
 queue has finished and ended in a place you'd like to go back to? I'm here to help you 
 do just that.                                                                          
                                                                                        
 A 'music snapshot' is a Spotify playlist that encapsulates a part of your music        
 playing history.                                                                       
                                                                                        
 Unfortunately, because of Spotify API limitations (no accessible history of played     
 songs) the song history comes from your Last.fm account.                               
                                                                                        
 To use the app, you need to first create a new Spotify OAuth app in its developer      
 dashboard and get Last.fm API keys by creating a new API account. You can then use     
 those values in the authorize subcommand, which will also save the underlying data on  
 your disk.                                                                             
                                                                                        
╭─ Options ────────────────────────────────────────────────────────────────────────────╮
│ --version      Show the version and exit.                                            │
│ --help         Show this message and exit.                                           │
╰──────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────────────╮
│ authorize  Authorize music_snapshot with Spotify and Last.fm.                        │
│ create     Create a new music snapshot (Spotify playlist).                           │
╰──────────────────────────────────────────────────────────────────────────────────────╯
```

## Authors
Developed and maintained by [Paweł Adamczak][pawelad].

Source code is available at [GitHub][github music_snapshot].

If you'd like to contribute, please take a look at the
[contributing guide].

Released under [Mozilla Public License 2.0][license].


[asciicast music_snapshot]: https://asciinema.org/a/689879
[black]: https://github.com/psf/black
[codecov music_snapshot]: https://app.codecov.io/github/pawelad/music_snapshot
[contributing guide]: ./CONTRIBUTING.md
[github music_snapshot]: https://github.com/pawelad/music_snapshot
[license]: ./LICENSE
[new last.fm api account]: https://www.last.fm/api/account/create
[pawelad]: https://pawelad.me/
[pep561]: https://peps.python.org/pep-0561/
[pipx]: https://github.com/pypa/pipx
[pypi music_snapshot]: https://pypi.org/project/music_snapshot/
[spotify developer dashboard]: https://developer.spotify.com/dashboard
[virtualenv]: https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/
