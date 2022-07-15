#libraries
library(rzmq)
library(xts)
library(quantmod)
library(nnet)

#init ZMQ sockets
context = init.context()
socket = init.socket(context, 'ZMQ_REP')
bind.socket(socket,"tcp://*:5555")

#create dataframe from a received string 
create_df <- function(data)
{
  df <- data.frame()
  first_split <- strsplit(data, "||", T)
  count <- nlevels(as.factor(first_split[[1]]))
  
  for(i in (1:count))
  {
    splt <- strsplit(as.character(as.factor(first_split[[1]])[i]), "|", T)
    df[i, "Date"] <- as.POSIXct(splt[[1]][1], format = "%Y-%m-%d %H:%M")
    df[i, "Open"] <- as.numeric(splt[[1]][2])
    df[i, "High"] <- as.numeric(splt[[1]][3])
    df[i, "Low"] <- as.numeric(splt[[1]][4])
    df[i, "Close"] <- as.numeric(splt[[1]][5])
    df[i, "Volume"] <- as.numeric(splt[[1]][6])
  }
  return(df)
}

#return predicted values based on dataframe using neural network
neural_net <- function(df) 
{
  df_xts <- xts(df[,c(-1)], order.by = as.POSIXct(paste(df[,c(1)]), format = "%Y-%m-%d %H:%M:%S"))
  
  df_xts$rsi <- RSI(df_xts$Close)
  df_xts$MACD <- MACD(df_xts$Close)
  df_xts$will <- williamsAD(df_xts[,2:4])
  df_xts$cci <-  CCI(df_xts[,2:4])
  df_xts$STOCH <- stoch(df_xts[,2:4])
  df_xts$Aroon <- aroon(df_xts[, 2:3])
  df_xts$ATR <- ATR(df_xts[, 2:4])
  
  df_xts$H_Return <- diff(log(df_xts$High))
  df_xts$L_Return <- diff(log(df_xts$Low))
  df_xts$C_Return <- diff(log(df_xts$Close))
  
  for(i in 1:(nrow(df_xts)-1))
  {
    df_xts[i,"H_Return"] <- df_xts[i + 1,"H_Return"]
    df_xts[i,"L_Return"] <- df_xts[i + 1,"L_Return"]
    df_xts[i,"C_Return"] <- df_xts[i + 1,"C_Return"]
  }
  
  
  model_high <- nnet(H_Return ~ Open + High + Low + Close + Volume + rsi + macd + MACD + will + cci + 
                       fastK + fastD + STOCH + aroonUp + aroonDn + Aroon + tr + atr + trueHigh + ATR, 
                     data = df_xts[1:(nrow(df_xts)-1)], maxit = 5000, size = 20, decay = 0.01, linout = 1)
  
  model_low <- nnet(L_Return ~ Open + High + Low + Close + Volume + rsi + macd + MACD + will + cci + 
                      fastK + fastD + STOCH + aroonUp + aroonDn + Aroon + tr + atr + trueHigh + ATR, 
                    data = df_xts[1:(nrow(df_xts)-1)], maxit = 5000, size = 20, decay = 0.01, linout = 1)
  
  model_close <- nnet(C_Return ~ Open + High + Low + Close + Volume + rsi + macd + MACD + will + cci + 
                        fastK + fastD + STOCH + aroonUp + aroonDn + Aroon + tr + atr + trueHigh + ATR, 
                      data = df_xts[1:(nrow(df_xts)-1)], maxit = 5000, size = 20, decay = 0.01, linout = 1)
  
  
  pred_h <- predict(model_high, newdata = df_xts[nrow(df_xts),(1:20)])  
  h_prediction <- exp(pred_h[1]) * df[nrow(df), "High"]
  
  pred_l <- predict(model_low, newdata = df_xts[nrow(df_xts),(1:20)])  
  l_prediction <- exp(pred_l[1]) * df[nrow(df), "Low"]
  
  pred_c <- predict(model_close, newdata = df_xts[nrow(df_xts),(1:20)])  
  c_prediction <- exp(pred_c[1]) * df[nrow(df), "Close"]
  
  pred_values <- paste(h_prediction, l_prediction, c_prediction, sep="|")
  
  return(pred_values)
}

data <- NULL

#main cycle
while (TRUE) {
  data <- receive.string(socket)
  print("waiting")
  if(!is.null(data))
  {
    df <- create_df(data)
    msg <- neural_net(df)
    print(msg)
    send.raw.string(socket, msg)
    data <- NULL
    df <- NULL
    msg <- NULL
  }
}
