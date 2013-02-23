# kapital: A pytgtk monopoly bot

Copyright (c) 2013 Gianni Tedesco

Released under the terms of GNU GPL version 3; see COPYING

---

## Intro
kapital is a semi-interactive monpoly bot. It's written in python and uses
pygtk to display information about it's status and to accept raw monpod
commands in the cases it can't handle.

At the moment it's designed for 1v1 bot vs bot games but it can be easily
tweaked to play against humans. Check monopbot for the server IP/port, by
default set to localhost:11234. One instance of the bot must be the player who
creates the game named 'robotwar'. the player limit is to be found in
monop/client.py :: Client::gameupdate() method.

## Strategy
The current strategy is very simple. It buys all properties it lands on and
always pays out of jail. If there's ever a funding shortfall then it first
mortgages properties that are not parts of monopolies in order for cheapest to
most expensive. It will then mortgage properties that are parts of monopolies.
Finally it sells levels of houses on developed monopolies. This procedure is
iterative, so that after it has sold all houses on a developed monopoly then it
will, as a last ditch effort, mortgage those properties.

When there is a surplus of cash it chooses to unmortgage estates, starting from
the cheapest. If no etates are mortgaged then it buys levels of houses at a
time whenever it can.

## Compatibility
This has been tested against monopd 0.9.3. There is a bug in monopd on 64bit
builds which causes incorrect estate prices to be sent to the client. This
causes erroneous behaviour in the bot which relies on the correct values,
unlike a human player who can read the descriptive display text sent over the
wire. The following patch fixes the issue.

```diff
--- a/src/game.cpp	2013-02-23 02:03:16.008164643 +0000
+++ b/src/game.cpp	2013-02-23 01:55:28.937479591 +0000
@@ -2138,7 +2138,7 @@
 				color = estateGroup->getStringProperty("color");
				 		}
						 
						 -		p->ioWrite("<estateupdate estateid=\"%d\" color=\"%s\" bgcolor=\"%s\" owner=\"%d\" houseprice=\"%d\" group=\"%d\" can_be_owned=\"%d\" can_toggle_mortgage=\"%d\" can_buy_houses=\"%d\" can_sell_houses=\"%d\" price=\"%ld\" rent0=\"%d\" rent1=\"%d\" rent2=\"%d\" rent3=\"%d\" rent4=\"%d\" rent5=\"%d\"/>", eTmp->id(), color.c_str(), bgColor.c_str(), (eTmp->owner() ? eTmp->owner()->id() : -1), eTmp->housePrice(), eTmp->group() ? eTmp->group()->id() : -1, eTmp->canBeOwned(), eTmp->canToggleMortgage(p), eTmp->canBuyHouses(p), eTmp->canSellHouses(p), eTmp->price(), eTmp->rentByHouses(0), eTmp->rentByHouses(1), eTmp->rentByHouses(2), eTmp->rentByHouses(3), eTmp->rentByHouses(4), eTmp->rentByHouses(5));
						 +		p->ioWrite("<estateupdate estateid=\"%d\" color=\"%s\" bgcolor=\"%s\" owner=\"%d\" houseprice=\"%d\" group=\"%d\" can_be_owned=\"%d\" can_toggle_mortgage=\"%d\" can_buy_houses=\"%d\" can_sell_houses=\"%d\" price=\"%d\" rent0=\"%d\" rent1=\"%d\" rent2=\"%d\" rent3=\"%d\" rent4=\"%d\" rent5=\"%d\"/>", eTmp->id(), color.c_str(), bgColor.c_str(), (eTmp->owner() ? eTmp->owner()->id() : -1), eTmp->housePrice(), eTmp->group() ? eTmp->group()->id() : -1, eTmp->canBeOwned(), eTmp->canToggleMortgage(p), eTmp->canBuyHouses(p), eTmp->canSellHouses(p), eTmp->price(), eTmp->rentByHouses(0), eTmp->rentByHouses(1), eTmp->rentByHouses(2), eTmp->rentByHouses(3), eTmp->rentByHouses(4), eTmp->rentByHouses(5));
						  		p->ioWrite(eTmp->oldXMLUpdate(p, true));
								 	}
									 }
```

## Further work
The bot needs to handle auctions, going in to debt due to chance/community
chest cards and trading.

## Dependencies:
 - Python 2.7
 - pygtk, pygobject, etc


## Support the author
If you like and use this software then press [<img src="http://www.paypalobjects.com/en_US/i/btn/btn_donate_SM.gif">](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=gianni%40scaramanga%2eco%2euk&lc=GB&item_name=Gianni%20Tedesco&item_number=scaramanga&currency_code=GBP&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted) to donate towards its development progress and email me to say what features you would like added.
