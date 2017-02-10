#Minimal WebPush Subscription Demo

This is the companion demo for How to Manage Web Push Subscriptions.


## Getting Started

 This demo was written on a Linux box. This means that macs may work too, but
 older installs of Windows might have a harder time of things.

  In addition, you'll need to either serve the `./page` directory from your
  local web server or run `bin/topic_server` with enough privileges to be able
  to start a web server at port 80. This is because of a restriction enforced
  by ServiceWorkers. ServiceWorker scripts must either be served from a
  secure server (one that can run `https://` or from `localhost`)


 To get started:
 ```
git clone https://github.com/jrconlin/topics.git
cd topics
virtualenv .
bin/activate
python setup.py develop
server
```

 Now start your browser and go to the topic `page` being served. (Again,
 either this is under a server running on your local machine , or by
 running
 `bin/server` and going to http://localhost:8200 )

 The page is fairly self explanatory, but basically, click on the ***Subscribe***
 button, and say "Allow" when prompted.

## Sending Messages

TBD: More words
