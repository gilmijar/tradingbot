CREATE TABLE `errorlog` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `errorModule` varchar(200) DEFAULT NULL,
  `errorClass` varchar(200) DEFAULT NULL,
  `errorCode` tinyint(3) unsigned DEFAULT NULL,
  `errorText` varchar(200) NOT NULL,
  `errorTimeStamp` int(11) NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `iErrorTimeStamp` (`errorTimeStamp`)
) ENGINE=Aria AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 PAGE_CHECKSUM=1 ROW_FORMAT=FIXED;
