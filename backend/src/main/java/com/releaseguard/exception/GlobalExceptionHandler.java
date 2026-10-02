package com.releaseguard.exception;

import com.releaseguard.ml.MlPredictionException;
import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log =
        LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiErrorResponse> handleValidation(
        MethodArgumentNotValidException exception,
        HttpServletRequest request
    ) {

        Map<String, String> details =
            new LinkedHashMap<>();

        exception.getBindingResult()
            .getFieldErrors()
            .forEach(error ->
                details.put(
                    error.getField(),
                    error.getDefaultMessage()
                )
            );

        ApiErrorResponse response =
            new ApiErrorResponse(
                OffsetDateTime.now(),
                HttpStatus.BAD_REQUEST.value(),
                "VALIDATION_ERROR",
                "Request validation failed",
                request.getRequestURI(),
                details
            );

        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(response);
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    public ResponseEntity<ApiErrorResponse> handleNotFound(
        ResourceNotFoundException exception,
        HttpServletRequest request
    ) {

        ApiErrorResponse response =
            new ApiErrorResponse(
                OffsetDateTime.now(),
                HttpStatus.NOT_FOUND.value(),
                "RESOURCE_NOT_FOUND",
                exception.getMessage(),
                request.getRequestURI(),
                null
            );

        return ResponseEntity
            .status(HttpStatus.NOT_FOUND)
            .body(response);
    }

    @ExceptionHandler(ConflictException.class)
    public ResponseEntity<ApiErrorResponse> handleConflict(
        ConflictException exception,
        HttpServletRequest request
    ) {

        ApiErrorResponse response =
            new ApiErrorResponse(
                OffsetDateTime.now(),
                HttpStatus.CONFLICT.value(),
                "CONFLICT",
                exception.getMessage(),
                request.getRequestURI(),
                null
            );

        return ResponseEntity
            .status(HttpStatus.CONFLICT)
            .body(response);
    }

    @ExceptionHandler(MlPredictionException.class)
    public ResponseEntity<ApiErrorResponse> handleMlPredictionFailure(
        MlPredictionException exception,
        HttpServletRequest request
    ) {

        ApiErrorResponse response =
            new ApiErrorResponse(
                OffsetDateTime.now(),
                HttpStatus.BAD_GATEWAY.value(),
                "ML_SERVICE_UNAVAILABLE",
                exception.getMessage(),
                request.getRequestURI(),
                null
            );

        return ResponseEntity
            .status(HttpStatus.BAD_GATEWAY)
            .body(response);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiErrorResponse> handleUnexpectedException(
        Exception exception,
        HttpServletRequest request
    ) {

        log.error(
            "Unexpected error while processing {} {}",
            request.getMethod(),
            request.getRequestURI(),
            exception
        );

        ApiErrorResponse response =
            new ApiErrorResponse(
                OffsetDateTime.now(),
                HttpStatus.INTERNAL_SERVER_ERROR.value(),
                "INTERNAL_SERVER_ERROR",
                "An unexpected error occurred",
                request.getRequestURI(),
                null
            );

        return ResponseEntity
            .status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(response);
    }
}
