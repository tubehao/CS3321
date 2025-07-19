# Database hw5

```
CREATE DATABASE my_database;
USE my_database;
```

![image-20250406184747545](/Users/hguan/Library/Application Support/typora-user-images/image-20250406184747545.png)

```
INSERT INTO StudentGrades (student_id, grade) VALUES (1, 85);
INSERT INTO StudentGrades (student_id, grade) VALUES (2, 73);
INSERT INTO StudentGrades (student_id, grade) VALUES (3, 91);
INSERT INTO StudentGrades (student_id, grade) VALUES (4, 67);
INSERT INTO StudentGrades (student_id, grade) VALUES (5, 59);
```

```
DELIMITER $$

CREATE PROCEDURE GradeDistribution()
BEGIN
    DECLARE v_0_60 INT DEFAULT 0;
    DECLARE v_60_70 INT DEFAULT 0;
    DECLARE v_70_80 INT DEFAULT 0;
    DECLARE v_80_90 INT DEFAULT 0;
    DECLARE v_90_100 INT DEFAULT 0;

    SELECT COUNT(*) INTO v_0_60 FROM StudentGrades WHERE grade BETWEEN 0 AND 59;
    SELECT COUNT(*) INTO v_60_70 FROM StudentGrades WHERE grade BETWEEN 60 AND 69;
    SELECT COUNT(*) INTO v_70_80 FROM StudentGrades WHERE grade BETWEEN 70 AND 79;
    SELECT COUNT(*) INTO v_80_90 FROM StudentGrades WHERE grade BETWEEN 80 AND 89;
    SELECT COUNT(*) INTO v_90_100 FROM StudentGrades WHERE grade BETWEEN 90 AND 100;

    SELECT CONCAT('0~59 分数段人数: ', v_0_60) AS result;
    SELECT CONCAT('60~69 分数段人数: ', v_60_70) AS result;
    SELECT CONCAT('70~79 分数段人数: ', v_70_80) AS result;
    SELECT CONCAT('80~89 分数段人数: ', v_80_90) AS result;
    SELECT CONCAT('90~100 分数段人数: ', v_90_100) AS result;
END $$

DELIMITER ;
```

```
CALL GradeDistribution();
-- 调用
```

![image-20250406184912766](/Users/hguan/Library/Application Support/typora-user-images/image-20250406184912766.png)
