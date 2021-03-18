DROP TABLE IF EXISTS `errorlog`;
CREATE TABLE IF NOT EXISTS `errorlog` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `errorModule` varchar(200) NULL,
  `errorClass`  varchar(200) NULL,
  `errorCode` tinyint unsigned NULL,
  `errorText` varchar(200) NOT NULL,
  `errorTimeStamp` int NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `iErrorTimeStamp` (`errorTimeStamp`)
) ENGINE=Aria DEFAULT CHARSET=utf8 ROW_FORMAT=FIXED;
