CREATE TABLE `placedOrder` (
  `ID` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `marketOrderId` int(11) UNSIGNED DEFAULT NULL, -- will not be given if the order is filled immediately
  `currencyPair` varchar(10) NOT NULL,
  `orderType` enum('ask','bid') NOT NULL COMMENT '0=ask, 1=bid',
  `amount` decimal(14,8) UNSIGNED NOT NULL,
  `price` decimal(14,8) UNSIGNED NOT NULL COMMENT 'exchange rate',
  `orderTimeStamp` int(11) UNSIGNED NOT NULL,
  `agent` varchar(16) NOT NULL COMMENT 'id or name of ''agent'', investment strategy that placed the order',
  PRIMARY KEY (`ID`),
  UNIQUE INDEX ui_placedOrder_marketOrderId (`marketOrderId`)
) ENGINE=InnoDB;
