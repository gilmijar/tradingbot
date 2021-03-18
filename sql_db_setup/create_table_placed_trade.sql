CREATE TABLE `placedTrade` (
  `ID` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `tradeId` int(11) UNSIGNED NOT NULL,
  `orderId` int(11) UNSIGNED DEFAULT NULL ,
-- 'order identifier\nfrom order object which is output of trade\nIF trade executed immediatly THEN entire order object is empty\nIF trade executed partially THEN order describe partial order\nIF trade not executed THEN order goes to orderbook and order object contains copy of input parameters',
  `baseCurrency` varchar(5) NOT NULL COMMENT 'The first listed currency of a currency pair - API trade output: currencyCrypto',
  `quoteCurrency` varchar(5) NOT NULL COMMENT 'The second listed currency of a currency pair - API trade output: currencyFiat',
  `baseAmount` decimal(14,8) UNSIGNED NOT NULL COMMENT 'amount of base currency traded',
  `price` decimal(14,8) UNSIGNED NOT NULL COMMENT 'exchange rate',
  `tradeType` enum('sell', 'buy') NOT NULL COMMENT '0=sell or 1=buy',
  `tradeTimeStamp` int(11) UNSIGNED NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `u_i_placedTrade_tradeId` (`tradeId`)
) ENGINE=InnoDB 

