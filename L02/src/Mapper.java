import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import java.util.Queue;

public class Mapper {
	public String root_directory;
	public List<String> fileNames;
	public Queue<String> directoryQ;
	public HashMap<String, Integer> hm;
	public char[] punctuation = { '\"', ',', '.', '!', '?', ';', ':'};
	public List<String> stop_words;
	public List<String> exceptions;

	public Mapper(String directory_path)
	{
		this.root_directory = new String(directory_path);
		this.fileNames  = new ArrayList<String>();
		this.directoryQ = new LinkedList<String>();
		this.directoryQ.add(this.root_directory);
		this.hm = new HashMap<String, Integer>();
		this.stop_words = new ArrayList<String>();
		File file = new File("stop_words.txt"); 
		BufferedReader br = null;
		try {
			br = new BufferedReader(new FileReader(file));
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} 
		String st; 
		try {
			while ((st = br.readLine()) != null) 
			{
				this.stop_words.add(st);
			}
		} catch (IOException e) {
			e.printStackTrace();
		} 		
		this.exceptions = new ArrayList<String>();
		file = new File("exceptions.txt"); 
		br = null;
		try {
			br = new BufferedReader(new FileReader(file));
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} 
		try {
			while ((st = br.readLine()) != null) 
			{
				this.exceptions.add(st);
			}
		} catch (IOException e) {
			e.printStackTrace();
		} 		
	}
	
	public boolean isPunctuation(char ch)
	{
		for (char c : punctuation) {
		    if (c == ch) 
		    {
		        return true;
		    }
		}
		return false;
	}
	
	public void getFiles()
	{
		
		while (!directoryQ.isEmpty())
		{
			File director = new File(directoryQ.element());
			directoryQ.remove();
			File[] listOfFiles = director.listFiles();
			
			for (File file : listOfFiles) {
			    if (file.isFile()) 
			    {
			    	fileNames.add(file.getPath());	// adaug fisier
			    }
			    if (file.isDirectory())
			    {
			    	directoryQ.add(file.getPath());
			    }
			}
		}
	}
	
	public void map()
	{
		for (String file : fileNames)
		{
			mapFile(file);
		}
	}
	
	public boolean isException(String word)
	{
		if (this.exceptions.indexOf(word) != -1)
		{
			return true;
		}
		return false;
	}
	
	public boolean isStopWord(String word)
	{
		if (this.stop_words.indexOf(word) != -1)
		{
			return true;
		}
		return false;
	}
	
	public void mapFile(String filename)
	{
		InputStream in = null;
		try {
			in = new FileInputStream(filename);
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}
        Reader reader = null;
		try {
			reader = new InputStreamReader(in, "UTF-8");
		} catch (UnsupportedEncodingException e1) {
			e1.printStackTrace();
		}
        int r;
        StringBuilder sb = new StringBuilder();
        StringBuilder lower_sb = new StringBuilder();
        try {
			while ((r = reader.read()) != -1) {
			    char ch = (char) r;
			    char lch = Character.toLowerCase(ch);
			    if (Character.isWhitespace(ch) || isPunctuation(ch))
			    {
			    	if (sb.length() != 0)	// doar daca stringul nu e gol
			    	{
				    	// daca e spatiu sau punctuatie, se termina cuvantul
				    	// adauga la HashMap
				    	String s = sb.toString();
				    	String lower_s = lower_sb.toString();
				    	if (isException(s))
				    	{
				    		// e exceptie					    	
				    		// nu e stop word
					    	int val = 0;
					    	if (hm.containsKey(s))
					    	{
					    		val = hm.get(s);
					    	}
					    	hm.put(s, val + 1);
					    	// reinitializeaza StringBuilderul
					    	sb = new StringBuilder();
					    	lower_sb = new StringBuilder();
				    	}
				    	else
				    	{
				    		if (!this.isStopWord(s))
					    	{
					    		// nu e stop word
						    	int val = 0;
						    	if (hm.containsKey(lower_s))
						    	{
						    		val = hm.get(lower_s);
						    	}
						    	hm.put(lower_s, val + 1);
						    	// reinitializeaza StringBuilderul
						    	sb = new StringBuilder();
						    	lower_sb = new StringBuilder();
					    	}
				    		else
				    		{
				    			sb = new StringBuilder();
				    			lower_sb = new StringBuilder();
				    		}
				    	}
			    	}
			    }
			    else
			    {
			    	sb.append(ch);
			    	lower_sb.append(lch);
			    }
			}
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	
	public static void main(String[] args) {
		Mapper m  = new Mapper("test-files");
		m.getFiles();
		m.map();
		for(String key: m.hm.keySet())
		{
			System.out.println(key + ": "+m.hm.get(key));
		}
	}

}
