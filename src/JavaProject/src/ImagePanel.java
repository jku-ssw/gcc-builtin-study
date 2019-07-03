import java.awt.Graphics;
import java.awt.image.BufferedImage;
import java.io.IOException;

import javax.imageio.ImageIO;
import javax.swing.JPanel;

public class ImagePanel extends JPanel {

	private static final long serialVersionUID = 1L;
	private BufferedImage image;

	@Override
	protected void paintComponent(Graphics g) {
		super.paintComponent(g);
		if (image != null) {
			g.drawImage(image.getScaledInstance(getWidth(),
					(int) (1.0 * image.getHeight() * getWidth() / image.getWidth()), 0), 0, 0, this);
		}
	}
	
	public void setImage(ImageFile imageFile) {
		if (imageFile == null) {
			image = null;
		} else {
			try {
				image = ImageIO.read(imageFile.path);
			} catch (IOException e) {
				throw new AssertionError(e);
			}
		}
		repaint();
	}

}