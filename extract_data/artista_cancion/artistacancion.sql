PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE canciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_artista INTEGER,
            artista TEXT,
            cancion TEXT,
            fecha_guardado TEXT,
            UNIQUE(id_artista, cancion)  -- Evitar duplicados
        );
INSERT INTO canciones VALUES(1,3409,'$.C.A.M.','Forever $cams','2025-02-16 23:50:53');
INSERT INTO canciones VALUES(2,3409,'$.C.A.M.','$cam Will','2025-02-16 23:51:06');
INSERT INTO canciones VALUES(3,3409,'$.C.A.M.','I Can’t Call It','2025-02-16 23:51:15');
INSERT INTO canciones VALUES(4,3409,'$.C.A.M.','$camwill 2','2025-02-16 23:51:29');
INSERT INTO canciones VALUES(5,3409,'$.C.A.M.','Long Live $camz','2025-02-16 23:51:36');
INSERT INTO canciones VALUES(6,3409,'$.C.A.M.','Ghazi Frstyl','2025-02-16 23:51:46');
INSERT INTO canciones VALUES(7,3409,'$.C.A.M.','Ready To $cam','2025-02-16 23:51:56');
INSERT INTO canciones VALUES(8,3409,'$.C.A.M.','Majin','2025-02-16 23:52:06');
INSERT INTO canciones VALUES(9,3409,'$.C.A.M.','LESGOO!','2025-02-16 23:52:12');
INSERT INTO canciones VALUES(10,3409,'$.C.A.M.','Score','2025-02-16 23:52:22');
INSERT INTO canciones VALUES(11,1599,'$IGA A','입에 마스크 (Mask On)','2025-02-16 23:53:03');
INSERT INTO canciones VALUES(12,1599,'$IGA A','고래를 위하여 (Blue Whale)','2025-02-16 23:53:08');
INSERT INTO canciones VALUES(13,1599,'$IGA A','장원급제 (Jang Won Geup Jae)','2025-02-16 23:53:16');
INSERT INTO canciones VALUES(14,1599,'$IGA A','Cowboy','2025-02-16 23:53:31');
INSERT INTO canciones VALUES(15,1599,'$IGA A','Django','2025-02-16 23:53:46');
INSERT INTO canciones VALUES(16,1599,'$IGA A','Callin','2025-02-16 23:53:56');
INSERT INTO canciones VALUES(17,1599,'$IGA A','EXIT','2025-02-16 23:54:04');
INSERT INTO canciones VALUES(18,1599,'$IGA A','알아 (I Know)','2025-02-16 23:54:19');
INSERT INTO canciones VALUES(19,1599,'$IGA A','Style (ToT)','2025-02-16 23:54:25');
INSERT INTO canciones VALUES(20,1599,'$IGA A','와신상담 (Patience) (Interlude)','2025-02-16 23:54:36');
INSERT INTO canciones VALUES(21,730,'''A'' Bomb','Calm Like a Bomb','2025-02-16 23:55:19');
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('canciones',21);
COMMIT;
