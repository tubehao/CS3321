# Database hw8
1. 创建 price_log 表和触发器：

```
# 创建price log表
CREATE TABLE price_log (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    product_id INT UNSIGNED NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# 创建product表
CREATE TABLE product (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10,2)
);

# 创建 TRIGGER
DELIMITER $$

CREATE TRIGGER before_price_update
BEFORE UPDATE ON product
FOR EACH ROW
BEGIN
    INSERT INTO price_log (product_id, price, update_time)
    VALUES (OLD.id, OLD.price, CURRENT_TIMESTAMP);
END$$

DELIMITER ;
```
![image-20250427141449596](/Users/hguan/Library/Application Support/typora-user-images/image-20250427141449596.png)

2. 创建 student_bf 表和删除触发器：

```
CREATE TABLE Student (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    age INT
);

CREATE TABLE student_bf (
    id INT NOT NULL,
    name VARCHAR(255),
    age INT,
    PRIMARY KEY (id)
);

DELIMITER $$
CREATE TRIGGER before_student_delete
BEFORE DELETE ON Student
FOR EACH ROW
BEGIN
    INSERT INTO student_bf (id, name, age)
    VALUES (OLD.id, OLD.name, OLD.age);
END$$
DELIMITER ;
```
![image-20250427141809488](/Users/hguan/Library/Application Support/typora-user-images/image-20250427141809488.png)

3. 创建 SC 表限制成绩的触发器：

```
CREATE TABLE SC (
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    score INT CHECK (score BETWEEN 0 AND 100),
    PRIMARY KEY (student_id, course_id)
);

DELIMITER $$
CREATE TRIGGER before_sc_insert
BEFORE INSERT ON SC
FOR EACH ROW
BEGIN
    IF NEW.score < 0 OR NEW.score > 100 THEN
        SET NEW.score = 0;
    END IF;
END$$
DELIMITER ;
```

![image-20250427142007953](/Users/hguan/Library/Application Support/typora-user-images/image-20250427142007953.png)
