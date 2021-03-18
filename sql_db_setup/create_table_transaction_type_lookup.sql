CREATE TABLE `transactionTypeLookup` (
  `orderType` enum('ask','bid') NOT NULL,
  `tradeType` enum('sell','buy') NOT NULL,
  PRIMARY KEY (`orderType`)
) ENGINE=InnoDB;


/* prototyp zapytania matchowania orderów z trade'ami
select * from placedTrade pt
join transactionTypeLookup ttl
on pt.tradeType = ttl.tradeType
join placedOrder po
on  po.orderType = ttl.orderType
and pt.tradeTimeStamp >= po.orderTimeStamp
and pt.price = po.price
and pt.baseAmount <= po.amount;
*/