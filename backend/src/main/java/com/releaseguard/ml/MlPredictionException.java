package com.releaseguard.ml;

public class MlPredictionException extends RuntimeException {

    public MlPredictionException(
        String message,
        Throwable cause
    ) {
        super(message, cause);
    }
}
