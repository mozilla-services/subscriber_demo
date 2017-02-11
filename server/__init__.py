""""
This applet mocks a subscription provider manager. It's sole task is to
accept an incoming new subscription request from a client page and record
the endpoint information. Obviously, there's A LOT that is NOT implemented
here, including subscription management. As is, this presumes only one user,
ever. You'll probably want to use some lovely User identification system for
that bit.

It also doesn't do any publication. That's handled by the pusher.
"""
