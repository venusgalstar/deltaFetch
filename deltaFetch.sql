/*
 Navicat Premium Data Transfer

 Source Server         : deltafetch
 Source Server Type    : MySQL
 Source Server Version : 80034 (8.0.34-0ubuntu0.20.04.1)
 Source Host           : localhost:3306
 Source Schema         : deltaFetch

 Target Server Type    : MySQL
 Target Server Version : 80034 (8.0.34-0ubuntu0.20.04.1)
 File Encoding         : 65001

 Date: 31/08/2023 16:55:41
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for task
-- ----------------------------
DROP TABLE IF EXISTS `task`;
CREATE TABLE `task`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'id',
  `jobid` int NOT NULL COMMENT 'jobid',
  `url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'url for monitor',
  `keyword` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'keyword for monitor',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'content',
  `xpath` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT 'watching tag',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for updated
-- ----------------------------
DROP TABLE IF EXISTS `updated`;
CREATE TABLE `updated`  (
  `id` int NOT NULL AUTO_INCREMENT,
  `jobid` int NOT NULL,
  `diff` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `timestamp` datetime NOT NULL,
  `search` int NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
