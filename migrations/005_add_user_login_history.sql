-- Add UserLoginHistory table to track all login/signup events
CREATE TABLE IF NOT EXISTS "userLoginHistory" (
    id VARCHAR(64) PRIMARY KEY,
    "userId" VARCHAR(64) NOT NULL,
    email VARCHAR(320),
    name TEXT,
    "loginMethod" VARCHAR(64) NOT NULL,
    action VARCHAR(32) NOT NULL,
    "profileImage" TEXT,
    "ipAddress" VARCHAR(64),
    "userAgent" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "timestamp" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS "userLoginHistory_userId_idx" ON "userLoginHistory"("userId");
CREATE INDEX IF NOT EXISTS "userLoginHistory_timestamp_idx" ON "userLoginHistory"("timestamp");
CREATE INDEX IF NOT EXISTS "userLoginHistory_isActive_idx" ON "userLoginHistory"("isActive");
