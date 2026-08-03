r <- sqrt(2) / 2
theta <- seq(0, 2 * pi, length.out = 400)
x <- r * cos(theta)
y <- r * sin(theta)

png("figures/circle.png", width = 800, height = 800, res = 150)
plot(x, y, type = "l", asp = 1, lwd = 2,
     xlab = "x", ylab = "y",
     main = expression(paste("Circle of radius ", sqrt(2)/2)))
abline(h = 0, v = 0, col = "grey80", lty = 2)
dev.off()
