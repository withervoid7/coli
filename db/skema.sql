drop table if exists Users;
create table if not exists Users(
    username varchar(30) primary key,
    password varchar(30)
);

create table if not exists note (
    id int auto_increment primary key,
    creator _username varchar(32),
    title varchar(200),
    content text,

    Foreign key (creator_username) references user(username)
);

insert int users (
    username, password
) values ('test','test');
