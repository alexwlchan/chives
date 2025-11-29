# chives

chives is a collection of Python functions for working with my local
media archives.

I store a lot of media archives as [static websites][static-sites], and I use Python scripts to manage the sites.
This includes:

*   Verifying every file that's described in the metadata is stored correctly
*   Downloading pages from sites I want to bookmark
*   Checking the quality and consistency of my metadata

This package has some functions I share across multiple archives/sites.

[static-sites]: https://alexwlchan.net/2024/static-websites/

## References

I've written blog posts about some of the code in this repo:

*   [Cleaning up messy dates in JSON](https://alexwlchan.net/2025/messy-dates-in-json/)
*   [Detecting AV1-encoded videos with Python](https://alexwlchan.net/2025/detecting-av1-videos/)

## Versioning

This library is monotically versioned.
I'll try not to break anything between releases, but I make no guarantees of back-compatibility.

I'm making this public because it's convenient for me, and you might find useful code here, but be aware this may not be entirely stable.

## Usage

See the docstrings on individual functions for usage descriptions.

## Installation

If you want to use this in your project, I recommend copying the relevant function and test into your codebase (with a link back to this repo).

Alternatively, you can install the package from PyPI:

```console
$ pip install alexwlchan-chives
```

## Development

If you want to make changes to the library, there are instructions in [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT.
