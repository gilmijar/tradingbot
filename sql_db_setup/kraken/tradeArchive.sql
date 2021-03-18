DROP TABLE IF EXISTS `tradeArchive`;

CREATE TABLE `tradeArchive` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `ticker` varchar(6) NOT NULL,
  `tradeId` bigint unsigned NOT NULL,
  `tradeType` tinyint(4) NOT NULL,
  `price` decimal(12,4) unsigned NOT NULL,
  `amount` decimal(14,8) unsigned NOT NULL,
  `tradeTimeStamp` int(11) NOT NULL,
  PRIMARY KEY (`ID`),
  UNIQUE KEY `iTradeId` (`ticker`,`tradeId`),
  KEY `iTradeTimeStamp` (`tradeTimeStamp`),
  KEY `iTradePrice` (`price`)
) ENGINE=Aria AUTO_INCREMENT=1 DEFAULT CHARSET=latin1 PAGE_CHECKSUM=1 ROW_FORMAT=FIXED;
