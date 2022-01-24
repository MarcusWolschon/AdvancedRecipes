<h1 align="center">
  <br>
  <a href="https://tandoor.dev"><img src="https://github.com/vabene1111/recipes/raw/develop/docs/logo_color.svg" height="256px" width="256px"></a>
  <br>
  Tandoor Recipes - Advanced
  <br>
</h1>

<h4 align="center">Improvements over the vanilla Tandoor Recipes:</h4>

This is my **personal fork** of [Tandoor Recipes](https://github.com/TandoorRecipes/recipes).
It includes serveral features I've written that where not or not yet accepted as pull requests upstream.
- [Improved developer instructions](https://github.com/TandoorRecipes/recipes/pull/1279)
- [Cookidoo importer with Thermomix handling](https://github.com/TandoorRecipes/recipes/pull/1389) (including highlight of Thermomix instructions from other recipe sources)
- [Import recipe steps](https://github.com/TandoorRecipes/recipes/pull/1303) (from sites with machine readable and also unformated steps)
- [Import recipe nutritional information](https://github.com/TandoorRecipes/recipes/pull/1294)
- WIP: [Handle common, problematic cases for ingredients](https://github.com/MarcusWolschon/AdvancedRecipes/issues/12)
- Planned: [Integrating with FatSecret calorie counter](https://github.com/MarcusWolschon/AdvancedRecipes/issues/2)

You can also find my [![app icon](https://raw.githubusercontent.com/MarcusWolschon/ShoppingForTandoor/main/app/ShoppingForTandoorDesktop/src/jvmMain/resources/favicon.ico) Android app for a shopping list](https://play.google.com/apps/testing/biz.wolschon.tandoorshopping.android) ([Source Code](https://github.com/MarcusWolschon/ShoppingForTandoor)).

**Timeline:** A stable release of both is planned after the (February 2022?) Release of the upstream Tandoor Recipes with the "Shopping List V2" feature.

<hr/>

<h4 align="center">The recipe manager that allows you to manage your ever growing collection of digital recipes.</h4>


## Installation

- [How to set up the software](docs/install/manual.md)
- [How to set up a development environment](docs/contribute.md)
- first step: After setting up your user, go to the "+" sign on the top, choose "import recipe" and drag the "bookmark this" into your bookmark bar/list. Then visit any recipe website, choose a recipe you like, click the bookmark and allow popups to easily start populating your personal recipe collection.

## Core Features
- 🥗 **Manage your recipes** - Manage your ever growing recipe collection
- 📆 **Plan** - multiple meals for each day
- 🛒 **Shopping lists V2** - via the meal plan or straight from recipes
- 📚 **Cookbooks** - collect recipes into books
- 👪 **Share and collaborate** on recipes with friends and family

## Made by and for power users

- 🔍 Powerful & customizable **search** with fulltext support and [TrigramSimilarity](https://docs.djangoproject.com/en/3.0/ref/contrib/postgres/search/#trigram-similarity)
- 🏷️ Create and search for **tags**, assign them in batch to all files matching certain filters
- ↔️ Quickly merge and rename ingredients, tags and units 
- 📥️ **Import recipes** from thousands of websites supporting [ld+json or microdata](https://schema.org/Recipe)
- ➗ Support for **fractions** or decimals
- 🐳 Easy setup with **Docker** and included examples for **Kubernetes**, **Unraid** and **Synology**
- 🎨 Customize your interface with **themes**
- 📦 **Sync** files with Dropbox and Nextcloud
  
## All the must haves

- 📱Optimized for use on **mobile** devices and also a **companion native Android app**
- 🌍 localized in many languages thanks to the awesome community
- 📥️ **Import your collection** from many other [recipe managers](https://docs.tandoor.dev/features/import_export/) including **special Cookidoo importer** for your personal, non-public receipt list
- ➕ Many more like recipe scaling, image compression, printing views and supermarkets

This application is meant for people with a collection of recipes they want to share with family and friends or simply
store them in a nicely organized way. A basic permission system exists but this application is not meant to be run as 
a public page.

## Contributing

You can help out with the ongoing development by looking for potential bugs in our code base, or by contributing new features. We are always welcoming new pull requests containing bug fixes, refactors and new features. We have a list of tasks and bugs on our issue tracker on Github. Please comment on issues if you want to contribute with, to avoid duplicating effort.

## License

Beginning with version 0.10.0 the code in this repository is licensed under the [GNU AGPL v3](https://www.gnu.org/licenses/agpl-3.0.de.html) license with a
[common clause](https://commonsclause.com/) selling exception. See [LICENSE.md](https://github.com/vabene1111/recipes/blob/develop/LICENSE.md) for details.

> NOTE: There appears to be a whole range of legal issues with licensing anything else then the standard completely open licenses.
> I am in the process of getting some professional legal advice to sort out these issues. 
> Please also see [Issue 238](https://github.com/vabene1111/recipes/issues/238) for some discussion and **reasoning** regarding the topic.

**Reasoning**  
**This software and *all* its features are and will always be free for everyone to use and enjoy.**

The reason for the selling exception is that a significant amount of time was spend over multiple years to develop this software.
A paid hosted version which will be identical in features and code base to the software offered in this repository will
likely be released in the future (including all features needed to sell a hosted version as they might also be useful for personal use).
This will not only benefit me personally but also everyone who self-hosts this software as any profits made through selling the hosted option
allow me to spend more time developing and improving the software for everyone. Selling exceptions are [approved by Richard Stallman](http://www.gnu.org/philosophy/selling-exceptions.en.html) and the
common clause license is very permissive (see the [FAQ](https://commonsclause.com/)).
