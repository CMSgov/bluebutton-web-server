BEGIN;
--
-- Add field code_challenge,  code_challenge_method, nonce, claims to grant
--
ALTER TABLE "oauth2_provider_grant"

ADD COLUMN "code_challenge" varchar(128) DEFAULT '' NOT NULL,

ADD COLUMN "code_challenge_method" varchar(10) DEFAULT '' NOT NULL,

ADD COLUMN "nonce" varchar(255) DEFAULT '' NOT NULL,

ADD COLUMN "claims" text DEFAULT '' NOT NULL;

ALTER TABLE "oauth2_provider_grant"

ALTER COLUMN "code_challenge" DROP DEFAULT,

ALTER COLUMN "code_challenge_method" DROP DEFAULT,

ALTER COLUMN "nonce" DROP DEFAULT,

ALTER COLUMN "claims" DROP DEFAULT;

--
-- Alter field redirect_uri on grant
--
ALTER TABLE "oauth2_provider_grant" ALTER COLUMN "redirect_uri" TYPE text USING "redirect_uri"::text;

--
-- Create model IDToken
--
CREATE TABLE "oauth2_provider_idtoken" ("id" bigserial NOT NULL PRIMARY KEY, "jti" uuid NOT NULL UNIQUE, "expires" timestamp with time zone NOT NULL, "scope" text NOT NULL, "created" timestamp with time zone NOT NULL, "updated" timestamp with time zone NOT NULL, "application_id" bigint NULL, "user_id" integer NULL);
--
-- Add field id_token to accesstoken
--
ALTER TABLE "oauth2_provider_accesstoken" ADD COLUMN "id_token_id" bigint NULL UNIQUE CONSTRAINT "oauth2_provider_acce_id_token_id_85db651b_fk_oauth2_pr" REFERENCES "oauth2_provider_idtoken"("id") DEFERRABLE INITIALLY DEFERRED; SET CONSTRAINTS "oauth2_provider_acce_id_token_id_85db651b_fk_oauth2_pr" IMMEDIATE;
ALTER TABLE "oauth2_provider_idtoken" ADD CONSTRAINT "oauth2_provider_idto_application_id_08c5ff4f_fk_dot_ext_a" FOREIGN KEY ("application_id") REFERENCES "dot_ext_application" ("id") DEFERRABLE INITIALLY DEFERRED;
ALTER TABLE "oauth2_provider_idtoken" ADD CONSTRAINT "oauth2_provider_idtoken_user_id_dd512b59_fk_auth_user_id" FOREIGN KEY ("user_id") REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED;
CREATE INDEX "oauth2_provider_idtoken_application_id_08c5ff4f" ON "oauth2_provider_idtoken" ("application_id");
CREATE INDEX "oauth2_provider_idtoken_user_id_dd512b59" ON "oauth2_provider_idtoken" ("user_id");

COMMIT;
