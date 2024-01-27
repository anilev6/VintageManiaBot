# VintageMania 🍑 - Personalized eBay Feed Bot

*Welcome to my small pet project!*

A go-to Telegram bot for eBay enthusiasts, [*beta-version*](https://t.me/FinderEbayBot).

The bot hourly checks eBay for items matching your specified searches and delivers them to your Telegram making an updating feed.

🥭 Limited Availability: Due to eBay API constraints, the service is exclusive to a limited number of users.
Currently supporting up to 26 users, each with the ability to create up to 8 personalized searches.

## Project Features

- OpenAI validates user input ensuring it is processed effectively
- eBay Developers Program Access gives authentic and reliable eBay data
- Admin panel and support infrastructure

### Getting Started

- `/start` the bot
- `/pause` the feed
- `/template` to see how to set-up a search
- `/help` to see all the commands

### Search Customization

Users are welcome to utilize eBay's [detailed URI parameters](https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search) for precise search customization.

🥭 It is possible to set-up `price_low`, `price_up`, `conditions`, and `buying_options` directly, without `filter`.

Note: if you use your custom `filter`, it will override your `price_low`, `price_up`, `conditions`, and `buying_options` search settings.

For these 4 parameters, default settings from `/template` apply if not specified.

### Spot a problem?

- `/support _your_query_here_` for assistance.

  Screenshots and images are welcome (the command has to be in the pic caption).

### Data Privacy & Safety

- `/forget_me` to erase all personal data, including Telegram account details, searches, and cached data.
  *Some data may persist in logs for a short period.*
- Log Rotation is automatic ensuring data security and minimal footprint.
- Preventing Harmful Content: using [one funny library](https://github.com/anilev6/easy-open-ai), all inputs are first screened for harmful content with ChatGPT before proceeding with search parameter validations.
