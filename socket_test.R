library(rzmq)

context = init.context()

socket = init.socket(context, 'ZMQ_REP')
bind.socket(socket,"tcp://*:5555")

data <- NULL


while (TRUE) {
  data <- receive.string(socket)
  if(!is.null(data))
  {
    print(data)
    #send.raw.string(socket, "World!")
    #data <- NULL
    break
  }
  
}

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
s <- "2022.07.10 10:31:23|2378|6736|3738|1234|20000||2022.07.10 10:30:29|2378|6736|3738|1234|20000||2022.07.10 10:32:20|2378|6736|3738|1234|20000||2022.07.10 10:33:29|2378|6736|3738|1234|20000"
df <- create_df(data)  
strsplit(s, "||", T)
  
  
  
  