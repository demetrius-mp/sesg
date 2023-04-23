## Using multiple clients at the same time

The client we provide is already very efficient, since it uses asynchronous programming to fetch many requests at the same time (at most 7 per second, to be exact).

However, you might think:

> What if I start 2 scripts that uses the same client, that would be twice as fast, right?

Well, you would be right if Scopus did not implement [Throttling Rates](https://dev.elsevier.com/api_key_settings.html).
Throttling rate is, in a few words, a strategy to limit the number of requests a user can fetch, in a given time period.
For the Scopus Search API, which is the one we use, this limit is 9 requests per second, per API key.
This is why i limited the client to fetch 7 requests per second at most.

So, if you start 2 scripts that uses the same client (which would be using the same API keys), 
it could be possible that the same API key is used to fetch more than 9 requests per second.

With that in mind, you could then just start each script with a different set of API keys.

But what if you want to use more than 2 clients at the same time? 
Would you manually split the API keys for the clients?

In this recipe, we propose a way to use as much clients as the user wants to, respecting the number of available API keys.

The idea is to use the builtin [`ThreadPoolExecutor`](https://docs.python.org/3.10/library/concurrent.futures.html#threadpoolexecutor)
to run all of the clients.
