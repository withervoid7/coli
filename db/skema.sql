drop table if exists Users;
create table if not exists Users(
    username varchar(30) primary key,
    password varchar(30)
);

insert into Users(username,password)
values ('Gaper','femboys');
