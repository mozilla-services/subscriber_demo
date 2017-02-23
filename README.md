#Minimal WebPush Subscription Demo

This is the companion demo for How to Manage Web Push Subscriptions.


## Getting Started

This demo was written on a Linux box. This means that macs may work
too, but older installs of Windows might have a harder time of things.

In addition, you'll need to either serve the `./page` directory from your
local web server or run `bin/server` and connect to
`http://localhost:8200`. This is because of a
restriction enforced by ServiceWorkers. ServiceWorker scripts must
either be served from a secure server (one that can run `https://` or
from `localhost`)


 To get started:
 ```
git clone https://github.com/mozilla-services/subscriber_demo.git
cd subscriber_demo
virtualenv -p python3 .
bin/activate
python setup.py develop
server
```

Now start your browser and go to the topic `page` being served.
(Again, either this is under a server running on your local machine , or by
running `bin/server` and going to http://localhost:8200 )

The page is fairly self explanatory, but basically, click on the
***Subscribe***
button, and say "Allow" when prompted.

## Sending Messages

To send a message to all registered subscribers, use the `pusher`
command:

`pusher --msg "This is a test"`

To send a message to a specific subscriber, specify that subscriber's
userID (displayed on the page after registration):

`pusher --msg "This is a test" --id='Abcd1234`

