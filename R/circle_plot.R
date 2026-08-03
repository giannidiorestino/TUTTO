r <- sqrt(2) / 2
theta <- seq(0, 2 * pi, length.out = 400)
x <- r * cos(theta)
y <- r * sin(theta)

lim <- c(-1.1, 1.1)

png("figures/circle.png", width = 800, height = 800, res = 150)
plot(x, y, type = "l", asp = 1, lwd = 2,
     xlim = lim, ylim = lim, axes = FALSE,
     xlab = "", ylab = "",
     main = expression(paste("Circle of radius ", sqrt(2)/2)))
arrows(lim[1], 0, lim[2], 0, length = 0.1)
arrows(0, lim[1], 0, lim[2], length = 0.1)
text(lim[2], 0, "x", pos = 3)
text(0, lim[2], "y", pos = 4)
abline(a = 1, b = -1, lwd = 2, col = "red")
points(c(0, 1), c(1, 0), pch = 19)
text(0, 1, "(0,1)", pos = 2)
text(1, 0, "(1,0)", pos = 4)

# Projective line [1:1/3]: line through the origin with direction ratio 1 : 1/3
abline(a = 0, b = (1 / 3) / 1, lwd = 2, col = "blue", lty = 2)
text(lim[2], lim[2] / 3, "[1:1/3]", pos = 1, col = "blue")
dev.off()
