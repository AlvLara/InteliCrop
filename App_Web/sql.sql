DROP TABLE IF EXISTS alertas;
DROP TABLE IF EXISTS logs_riego;
DROP TABLE IF EXISTS conf_umbrales;
DROP TABLE IF EXISTS cultivo;
DROP TABLE IF EXISTS usuario;


CREATE TABLE usuario (
    user_uuid CHAR(36) NOT NULL DEFAULT (UUID()),
    email VARCHAR(100) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT usuario_pk PRIMARY KEY (user_uuid),
    CONSTRAINT usuario_email_unique UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE cultivo (
    uuid_cultivo CHAR(36) NOT NULL DEFAULT (UUID()),
    user_uuid CHAR(36) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    secreto_cifrado VARCHAR(700) NOT NULL,
    estado_del_cultivo ENUM('activo', 'inactivo') DEFAULT 'activo',
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    api_key_hash VARCHAR(64) NOT NULL,

    CONSTRAINT cultivo_pk PRIMARY KEY (uuid_cultivo),
    CONSTRAINT cultivo_api_key_hash_unique UNIQUE (api_key_hash),
    CONSTRAINT cultivo_usuario_fk
        FOREIGN KEY (user_uuid)
        REFERENCES usuario(user_uuid)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE alertas (
    uuid_alerta CHAR(36) NOT NULL DEFAULT (UUID()),
    uuid_cultivo CHAR(36) NOT NULL,
    tipo_alerta VARCHAR(50) NOT NULL,
    mensaje TEXT NOT NULL,
    leida bool NOT NULL DEFAULT false,
    momento_alerta TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT alertas_pk PRIMARY KEY (uuid_alerta),

    CONSTRAINT alertas_cultivo_fk
        FOREIGN KEY (uuid_cultivo)
        REFERENCES cultivo(uuid_cultivo)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE logs_riego (
    uuid_comando CHAR(36) NOT NULL DEFAULT (UUID()),
    uuid_cultivo CHAR(36) NOT NULL,
    origen VARCHAR(50) NOT NULL,
    accion VARCHAR(100) NOT NULL,
    momento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT logs_riego_pk PRIMARY KEY (uuid_comando),

    CONSTRAINT logs_riego_cultivo_fk
        FOREIGN KEY (uuid_cultivo)
        REFERENCES cultivo(uuid_cultivo)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE conf_umbrales (
    uuid_conf CHAR(36) NOT NULL DEFAULT (UUID()),
    uuid_cultivo CHAR(36) NOT NULL,
    tipo_sensor VARCHAR(50) NOT NULL,
    min_valor FLOAT NOT NULL,
    max_valor FLOAT NOT NULL,
    notificar_alerta bool NOT NULL DEFAULT TRUE,
    riego_automatico BOOL NOT NULL DEFAULT FALSE,

    CONSTRAINT conf_umbrales_pk PRIMARY KEY (uuid_conf),

    CONSTRAINT conf_umbrales_cultivo_fk
        FOREIGN KEY (uuid_cultivo)
        REFERENCES cultivo(uuid_cultivo)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    CONSTRAINT conf_umbrales_valores_check
        CHECK (min_valor <= max_valor)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;