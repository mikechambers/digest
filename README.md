# Digest

Digest is a Python3 script that creates a local version of the weekly Economist magazine that aims to provide an improved reading and listening experience.

Specifically, it:

* Creates a local archive of the weekly edition
* Provides an optimized reading experience
* Easy navigation between sections and articles
* Ability to read offline
* Ability to easy jump to articles on Economist website
* Ability to listen to edition as a podcast, online or off

The project was built to work around performance issues and limitation of the Economist website and mobile application. 

This project requires that you have access to the digital version of the Economist, and is not affiliated with or supported by The Economist.

## Installation

The script requires Python3 and the following libraries to be installed.

```bash
pip install requests
pip install browsercookie
pip install readability-lxml
pip install lxml_html_clean
pip install readtime
```

## Usage

Before running the script, you must log into economist.com with an account that has access to the weekly edition, using one of the following browsers:

* Firefox (firefox)
* Google Chrome (chrome)
* Microsoft Edge (edge)
* Opera (opera)

and make sure to pass to the script like so:

```bash
python3 digest.py --output-dir ~/tmp/economist/ --cookie-source chrome
```

This is necessary to set the cookies for the script that will authenticate your account.

This will generate a folder in the form of **YYYY-MM-DD** in the specified output directory. The folder will contain an *index.html* file which can be loaded into a browser to access all of the content.

You can find a complete list of options by running:

```bash
python3 digest.py --help
```

## Using the Generated Podcast feed

An XML file will be generated that creates a podcast from the mp3 files for the current weekly edition. It is generated in serial mode with the order of the episodes based on the order of the articles online.

This file can be used to create a podcast to listen through the weekly edition, as well as sync all of the files offline to listen when you don't have network coverage.

Each podcast / URL represents a single weekly edition, and you will need to generate and add a new url for new editions.

You can find info on how to add the URL to Apple podcast [here](https://podcasters.apple.com/support/828-test-your-podcast)

Note that the mp3 files are not downloaded by the script, but rather they are linked to their online location.

Also, in order to add the URL to your podcasting app, you may need to host it online when you add it.

## Known Issues

The weekly cartoon does not currently display.

## Questions, Feature Requests, Feedback

If you have any questions, feature requests, need help, or just want to chat, you can ping me on [Twitter](https://twitter.com/mesh) or via email at [mikechambers@gmail.com](mailto:mikechambers@gmail.com).

You can also log bugs and feature requests on the [issues page](https://github.com/mikechambers/digest/issues).

## License

Project released under a [MIT License](LICENSE.md).

[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg)](LICENSE.md)
