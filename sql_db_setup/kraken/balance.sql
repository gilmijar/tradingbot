DROP TABLE IF EXISTS `balance`;

CREATE TABLE `balance` (
  `balanceTimeStamp` int(11) NOT NULL,
  `btc` decimal(15,8) NOT NULL DEFAULT '0.00000000',
  `eur` decimal(15,8) NOT NULL DEFAULT '0.00000000',
  `price` decimal(15,8) DEFAULT NULL,
  PRIMARY KEY (`balanceTimeStamp`)
) ENGINE=Aria DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1 ROW_FORMAT=FIXED;
