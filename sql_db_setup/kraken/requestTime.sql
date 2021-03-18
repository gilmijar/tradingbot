CREATE TABLE `requestTime` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `requestType` int(10) unsigned NOT NULL COMMENT 'types:\npublic requests:\n0 - trades\n1 - orderbook\nprivate requests:\n10 - open trades\n11 - balance\n12 - history',
  `sent` double unsigned NOT NULL,
  `received` double unsigned DEFAULT NULL,
  `duration` double unsigned DEFAULT NULL,
  `wasTimedOut` tinyint(3) unsigned DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=Aria AUTO_INCREMENT=1 DEFAULT CHARSET=latin1 PAGE_CHECKSUM=1;

